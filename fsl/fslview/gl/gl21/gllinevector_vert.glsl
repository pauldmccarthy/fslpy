/*
 * OpenGL vertex shader used for rendering GLLineVector instances.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

uniform mat4 voxToDisplayMat;
uniform vec3 imageShape;

attribute vec3 vertex;

varying vec3 fragVoxCoord;
varying vec3 fragTexCoord;

void main(void) {

  // TODO check voxel +0.5 offset

  // Round the vertex position to the nearest integer -
  // this gives us the corresponding voxel coordinates
  fragVoxCoord = floor(vertex + 0.5);

  // Transform the voxel coordinates to texture
  // coordinates, adding 0.5 to centre them
  fragTexCoord = (fragVoxCoord + 0.5) / imageShape;

  gl_Position = gl_ModelViewProjectionMatrix * vec4(vertex, 1);
}
