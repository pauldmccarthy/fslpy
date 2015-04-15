/*
 * OpenGL vertex shader used for rendering GLLineVector instances.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

uniform mat4 voxToDisplayMat
uniform vec3 imageShape;

attribute vec3 vertex;

varying vec3 fragVoxCoord;
varying vec3 fragTexCoord;

void main(void) {

  // TODO check voxel +0.5 offset
  fragVoxCoord = floor(vertex);
  fragTexCoord = fragVoxCoord / imageShape;

  gl_Position = gl_ModelViewProjectionMatrix * voxToDisplayMat * vec4(vertex, 1);
}
