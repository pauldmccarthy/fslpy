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


uniform vec3 imageDims;

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
  vec3 vertexPos = fragVoxCoords - 0.5;
  vec3 tensorVec;

  /*
   * Retrieve the tensor values for this voxel
   */
  if (useSpline) {
    tensorVec.x = spline_interp(imageTexture, voxCoords, imageShape, 0);
    tensorVec.y = spline_interp(imageTexture, voxCoords, imageShape, 1);
    tensorVec.z = spline_interp(imageTexture, voxCoords, imageShape, 2);
  }

  else {
    tensorVec = texture3D(imageTexture, voxCoords).xyz;
  }

  /*
   * Tranasform the tensor values  from their
   * texture range of [0,1] to the original
   * data range
   */
  tensorVec.xyz *= imageValueXform[0].x;
  tensorVec.xyz += imageValueXform[0].w; 

  /*
   * Vertices are coming in as line pairs - flip
   * every second vertex about the origin
   */
  if (mod(vertexID, 2) == 1) 
    tensorVec = -tensorVec;

  /*
   * Scale the vector by the minimum voxel length,
   * so it is a unit vector within real world space 
   */
  tensorVec /= imageDims / min(imageDims.x, min(imageDims.y, imageDims.z));

  /*
   * Offset the vertex position 
   * by the tensor direction
   */ 
  vertexPos += 0.5 * tensorVec;

  /*
   * Output the final vertex position
   */
  gl_Position = gl_ModelViewProjectionMatrix * 
                worldToWorldMat * 
                voxToDisplayMat * 
                vec4(vertexPos, 1);
}
