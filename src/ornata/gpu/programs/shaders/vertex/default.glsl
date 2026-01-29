#version 460 core
layout(location=0) in vec3 aPos;
layout(location=1) in vec3 aNrm;
layout(location=2) in vec2 aUV;
layout(location=3) in uint aTransformIndex;

layout(std140, binding=0) uniform CameraUBO {
    mat4 uView; mat4 uProj; mat4 uViewProj;
    vec3 uCameraPos; float uExposure;
    vec2 uViewport;  float uTime; uint uFrameIndex;
};
layout(std430, binding=1) buffer ModelMats { mat4 uModel[]; };

out VS_OUT { vec3 wPos; vec3 wNrm; vec2 uv; } vs;

void main() {
    mat4 M = uModel[aTransformIndex];
    vec4 wp = M * vec4(aPos,1.0);
    vs.wPos = wp.xyz;
    vs.wNrm = normalize(mat3(transpose(inverse(M))) * aNrm);
    vs.uv   = aUV;
    gl_Position = uViewProj * wp;
}
