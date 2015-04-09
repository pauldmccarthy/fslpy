#version 120

uniform sampler1D colourTexture;
uniform sampler3D imageTexture;
uniform mat4      voxValueXform;

varying vec3 fragTexCoord;

void main(void) {

  float value = texture3D(imageTexture, fragTexCoord).x;

  value = (voxValueXform * vec4(value, 0, 0, 0)).x;

  gl_FragColor = texture1D(colourTexture, value);
}
