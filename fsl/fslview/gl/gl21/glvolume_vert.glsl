/*
 * OpenGL vertex shader used for rendering GLVolume instances.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

attribute vec3 vertex;
attribute vec3 voxCoord;

varying vec3 fragVoxCoord;

void main(void) {

  fragVoxCoord = voxCoord;

  gl_Position = gl_ModelViewProjectionMatrix * vec4(vertex, 1);
}
