#version 460 core
layout(location=0) out vec4 FragColor;
in VS_OUT { vec3 wPos; vec3 wNrm; vec2 uv; } fs;

layout(binding=0) uniform sampler2D uAlbedo;
layout(std140, binding=2) uniform MaterialUBO {
    vec4  uTint; float uRough; float uMetal; int uACES; float uGamma;
};

vec3 aces(vec3 x){ const float a=2.51,b=0.03,c=2.43,d=0.59,e=0.14; return clamp((x*(a*x+b))/(x*(c*x+d)+e),0.0,1.0); }

void main() {
    vec3 N = normalize(fs.wNrm);
    vec3 base = texture(uAlbedo, fs.uv).rgb * uTint.rgb;
    // (Hook for full PBR/IBL could be added here)
    vec3 color = (uACES!=0) ? aces(base) : (uGamma>0.0 ? pow(base, vec3(1.0/uGamma)) : base);
    FragColor = vec4(color, uTint.a);
}
