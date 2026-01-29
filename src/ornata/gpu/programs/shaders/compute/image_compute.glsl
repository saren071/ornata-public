#version 460 core
#extension GL_KHR_shader_subgroup : enable

// Workgroup size tuned for cache-friendly 16x16 tiles
layout (local_size_x = 16, local_size_y = 16, local_size_z = 1) in;

// Use 16F for bandwidth unless you truly need fp32
layout (binding = 0, rgba16f) uniform readonly  image2D uInput;
layout (binding = 1, rgba16f) uniform writeonly image2D uOutput;

layout (std140, binding = 2) uniform CameraUBO {
    mat4  uView;
    mat4  uProj;
    mat4  uViewProj;
    vec3  uCameraPos; float uExposure;
    vec2  uViewport;  float uTime; uint uFrameIndex;
};

shared vec4 tile[16+2][16+2];

vec3 aces(vec3 x){
    const float a=2.51,b=0.03,c=2.43,d=0.59,e=0.14;
    return clamp((x*(a*x+b))/(x*(c*x+d)+e),0.0,1.0);
}

void main() {
    ivec2 size = imageSize(uOutput);
    ivec2 gid  = ivec2(gl_GlobalInvocationID.xy);
    if (any(greaterThanEqual(gid,size))) return;

    // Clamp coords when loading halo
    ivec2 base = gid - ivec2(1);
    for (int dy=0; dy<3; ++dy)
    for (int dx=0; dx<3; ++dx) {
        ivec2 c = clamp(base + ivec2(dx,dy), ivec2(0), size - ivec2(1));
        tile[gl_LocalInvocationID.y + dy][gl_LocalInvocationID.x + dx] = imageLoad(uInput, c);
    }
    // Ensure tile is ready
    barrier();

    vec4 center = tile[gl_LocalInvocationID.y+1][gl_LocalInvocationID.x+1];
    vec3 blur = (
        tile[gl_LocalInvocationID.y+1][gl_LocalInvocationID.x+1].rgb * 4.0 +
        tile[gl_LocalInvocationID.y+1][gl_LocalInvocationID.x+0].rgb +
        tile[gl_LocalInvocationID.y+1][gl_LocalInvocationID.x+2].rgb +
        tile[gl_LocalInvocationID.y+0][gl_LocalInvocationID.x+1].rgb +
        tile[gl_LocalInvocationID.y+2][gl_LocalInvocationID.x+1].rgb
    ) / 8.0;

    vec3 sharpen = center.rgb * 1.6 - blur * 0.6;

    // Subgroup average luma for adaptive mixing
    float l = dot(center.rgb, vec3(0.2126,0.7152,0.0722));
    float avgL = subgroupAdd(l) / float(subgroupSize());

    float w = smoothstep(0.05, 0.25, avgL);
    vec3 outRGB = mix(blur, sharpen, w);

    // Optional tonemap to LDR if you store to LDR later in pipe:
    outRGB = aces(outRGB * uExposure);

    imageStore(uOutput, gid, vec4(outRGB, center.a));
}
