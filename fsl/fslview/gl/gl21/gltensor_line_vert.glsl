/*
 * OpenGL vertex shader used for rendering GLObject instances.
 *
 * All this shader does is transfer texture coordinates through
 * to the fragment shader.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

#pragma include common_vert.glsl
#pragma include spline_interp.glsl

/*
 * Tensor image containing XYZ vectors
 */
uniform sampler3D imageTexture;


/*
 *
 */
uniform mat4 imageValueXform;


uniform mat4 voxToDisplayMat;

/*
 * Image/texture dimensions
 */
uniform vec3 imageShape;

/*
 * Vertex index - the built-in gl_VertexID
 * variable is not available in GLSL 120
 */
attribute float vertexID;

/*
 * Use spline interpolation?
 */
uniform bool useSpline;

void main(void) {

  common_vert();

  vec3 voxCoords = fragVoxCoords / imageShape;
  vec3 vertexPos = fragVoxCoords;
  vec3 tensorVec;
  
  if (useSpline) {
    tensorVec.x = spline_interp(imageTexture, voxCoords, imageShape, 0);
    tensorVec.y = spline_interp(imageTexture, voxCoords, imageShape, 1);
    tensorVec.z = spline_interp(imageTexture, voxCoords, imageShape, 2);
  }

  else {
    tensorVec = texture3D(imageTexture, voxCoords).xyz;
  }

  tensorVec.x = (imageValueXform * vec4(tensorVec.x, 0, 0, 1)).x;
  tensorVec.y = (imageValueXform * vec4(tensorVec.y, 0, 0, 1)).x;
  tensorVec.z = (imageValueXform * vec4(tensorVec.z, 0, 0, 1)).x;

  if (mod(vertexID, 2) == 0.0) tensorVec =  0.5 * tensorVec;
  else                         tensorVec = -0.5 * tensorVec;

  vertexPos += tensorVec;

  vertexPos -= 0.5;

  gl_Position = gl_ModelViewProjectionMatrix * 
                worldToWorldMat * 
                voxToDisplayMat * 
                vec4(vertexPos, 1);
}
