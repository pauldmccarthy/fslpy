#version 120

uniform sampler2D tex;

varying vec2 texCoord;

void main(void) {

  gl_FragColor = texture2D(tex, texCoord);
}
