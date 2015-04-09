/*
 * OpenGL vertex shader used for rendering GLVolume instances.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

attribute vec3 vertex;
attribute vec3 voxCoord;
attribute vec3 texCoord;

varying vec3 fragVoxCoord;
varying vec3 fragTexCoord;

void main(void) {

  fragVoxCoord = voxCoord;
  fragTexCoord = texCoord;

  gl_Position = gl_ModelViewProjectionMatrix * vec4(vertex, 1);
}
