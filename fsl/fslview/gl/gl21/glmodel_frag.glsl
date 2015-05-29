#version 120

#pragma include sobel.glsl

uniform sampler2D tex;

uniform float texWidth;
uniform float texHeight;

varying vec2 texCoord;

void main(void) {

  vec4 colour   = texture2D(tex, texCoord);
  vec4 filtered = sobel(tex, texWidth, texHeight, texCoord);

  if (filtered.w == 0)
    colour = vec4(0, 0, 0, 0);
  
  gl_FragColor  = colour;
}

