#version 460
#extension GL_EXT_ray_tracing : require
hitAttributeEXT vec2 bary;
layout(location=0) rayPayloadInEXT vec3 radiance;
void main(){ radiance = vec3(0.8, 0.8, 0.8); }
