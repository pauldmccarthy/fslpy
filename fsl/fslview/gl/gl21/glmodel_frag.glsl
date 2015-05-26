#version 120

#pragma include sobel.glsl

uniform sampler2D tex;

uniform float texWidth;
uniform float texHeight;

varying vec2 texCoord;

void main(void) {

  gl_FragColor = sobel(tex, texWidth, texHeight, texCoord);
  // gl_FragColor = texture2D(tex, texCoord);
}

