#version 460
#extension GL_EXT_ray_tracing : require

layout(set=0, binding=0) uniform accelerationStructureEXT uTLAS;
layout(set=0, binding=1, rgba16f) uniform image2D uOut;

layout(location=0) rayPayloadEXT vec3 radiance;

void main(){
    ivec2 px = ivec2(gl_LaunchIDEXT.xy);
    ivec2 sz = ivec2(gl_LaunchSizeEXT.xy);

    vec2 uv = (vec2(px) + 0.5) / vec2(sz);
    vec3 ro = vec3(0,0,0);
    vec3 rd = normalize(vec3(uv*2.0 - 1.0, 1.0));

    radiance = vec3(0);
    traceRayEXT(uTLAS, gl_RayFlagsOpaqueEXT, 0xFF, 0, 0, 0, ro, 0.001, rd, 1e38, 0);
    imageStore(uOut, px, vec4(radiance, 1));
}
