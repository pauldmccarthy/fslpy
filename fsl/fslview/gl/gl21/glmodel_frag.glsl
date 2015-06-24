#version 120

#pragma include edge.glsl

uniform sampler2D tex;

uniform float texWidth;
uniform float texHeight;

varying vec2  texCoord;

void main(void) {
  
  vec4 colour  = texture2D(tex, texCoord);

  // TODO offsets should be a user-settable parameter
  vec2 offsets = 1.0 / vec2(texWidth, texHeight);
  vec4 tol     = 1.0 / vec4(255, 255, 255, 255);

  if (edge2D(tex, texCoord, colour, tol, offsets)) gl_FragColor   = colour;
  else                                             gl_FragColor.a = 0.0;
}
