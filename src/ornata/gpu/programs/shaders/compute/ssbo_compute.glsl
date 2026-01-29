#version 460 core
#extension GL_KHR_shader_subgroup : enable

layout (local_size_x = 256, local_size_y = 1, local_size_z = 1) in;

struct Particle {
    vec4 pos;   // xyz = position, w = lifetime
    vec4 vel;   // xyz = velocity, w = mass
    vec4 col;   // rgba color (linear)
};

layout (std430, binding = 0) buffer ParticlesInOut { Particle p[]; };
layout (std430, binding = 1) buffer IndicesAlive  { uint alive[]; };
layout (std430, binding = 2) buffer IndicesDead   { uint dead[];  };

layout (std140, binding = 3) uniform SimUBO {
    vec3  gravity;      float dt;
    vec3  boundsMin;    float damping;
    vec3  boundsMax;    uint  maxCount;
    uint  resetOnDeath; float spawnEnergy; float time; uint frameIndex;
};

uint laneMaskAll() { return 0xFFFFFFFFu; }

void main() {
    uint idx = gl_GlobalInvocationID.x;
    if (idx >= maxCount) return;

    Particle s = p[idx];

    // Integrate (semi-implicit Euler)
    s.vel.xyz += gravity * dt;
    s.pos.xyz += s.vel.xyz * dt;

    // AABB collide + damping
    for (int axis=0; axis<3; ++axis) {
        if (s.pos[axis] < boundsMin[axis]) {
            s.pos[axis] = boundsMin[axis]; s.vel[axis] = -s.vel[axis]*damping;
        } else if (s.pos[axis] > boundsMax[axis]) {
            s.pos[axis] = boundsMax[axis]; s.vel[axis] = -s.vel[axis]*damping;
        }
    }

    // Lifetime
    s.pos.w -= dt; // w stores lifetime
    bool aliveNow = (s.pos.w > 0.0);

    // Write back updated particle
    p[idx] = s;

    // Subgroup compaction: write index into alive/dead lists
    uint ballot = subgroupBallot(aliveNow).x; // mask for first 32 lanes (portable enough)
    uint aliveCount = subgroupBallotBitCount(ballot);
    uint lane      = gl_SubgroupInvocationID;

    // Prefix within subgroup
    uint laneMask = (1u << lane) - 1u;
    uint localRankAlive = aliveNow ? subgroupBallotBitCount(ballot & laneMask) : 0u;
    uint localRankDead  = aliveNow ? 0u : subgroupBallotBitCount((~ballot) & laneMaskAll() & laneMask);

    // One lane reserves space for the subgroup in the global lists
    uint baseAlive = 0u, baseDead = 0u;
    if (lane == 0u) {
        baseAlive = atomicAdd(alive[0], aliveCount);            // alive[0] stores count head
        baseDead  = atomicAdd(dead[0],  subgroupSize()-aliveCount); // dead[0] stores count head
    }
    baseAlive = subgroupBroadcastFirst(baseAlive);
    baseDead  = subgroupBroadcastFirst(baseDead);

    if (aliveNow) {
        alive[baseAlive + localRankAlive + 1u] = idx; // +1 skip counter slot
    } else {
        dead[baseDead + localRankDead + 1u] = idx;
        if (resetOnDeath != 0u) {
            // Cheap respawn
            Particle r = s;
            r.pos.xyz = mix(boundsMin, boundsMax, vec3(fract(sin(float(idx)*12.9898 + time)*43758.5453)));
            r.vel.xyz = normalize(vec3(fract(sin(float(idx)*78.233 + time)*19341.0)) * 2.0 - 1.0) * spawnEnergy;
            r.pos.w   = 5.0 + fract(sin(float(idx)*3.11))*5.0; // lifetime reset
            p[idx]    = r;
            // mark as alive by pushing into alive list too
            uint push = atomicAdd(alive[0], 1u);
            alive[push + 1u] = idx;
        }
    }
}
