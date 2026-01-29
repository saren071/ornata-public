#version 460 core
layout(triangles) in;
layout(triangle_strip, max_vertices=3) out;

in VS_OUT { vec3 wPos; vec3 wNrm; vec2 uv; } gIn[];
out vec3 wPos; out vec3 wNrm; out vec2 uv;

void main(){
    for(int i=0;i<3;i++){
        wPos=gIn[i].wPos; wNrm=gIn[i].wNrm; uv=gIn[i].uv;
        gl_Position = gl_in[i].gl_Position;
        EmitVertex();
    }
    EndPrimitive();
}
