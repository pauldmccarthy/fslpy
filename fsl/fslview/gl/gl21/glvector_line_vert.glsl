/*
 * OpenGL vertex shader used for rendering GLVector instances.
 *
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

#pragma include common_vert.glsl
#pragma include spline_interp.glsl

/*
 * Vector image containing XYZ magnitudes
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
  vec3 vector;

  /*
   * Retrieve the vector values for this voxel
   */
  if (useSpline) {
    vector.x = spline_interp(imageTexture, voxCoords, imageShape, 0);
    vector.y = spline_interp(imageTexture, voxCoords, imageShape, 1);
    vector.z = spline_interp(imageTexture, voxCoords, imageShape, 2);
  }

  else {
    vector = texture3D(imageTexture, voxCoords).xyz;
  }

  /*
   * Tranasform the vector values  from their
   * texture range of [0,1] to the original
   * data range
   */
  vector.xyz *= imageValueXform[0].x;
  vector.xyz += imageValueXform[0].w; 

  /*
   * Vertices are coming in as line pairs - flip
   * every second vertex about the origin
   */
  if (mod(vertexID, 2) == 1) 
    vector = -vector;

  /*
   * Scale the vector by the minimum voxel length,
   * so it is a unit vector within real world space 
   */
  vector /= imageDims / min(imageDims.x, min(imageDims.y, imageDims.z));

  /*
   * Offset the vertex position 
   * by the vector direction
   */ 
  vertexPos += 0.5 * vector;

  /*
   * Output the final vertex position
   */
  gl_Position = gl_ModelViewProjectionMatrix * 
                worldToWorldMat * 
                voxToDisplayMat * 
                vec4(vertexPos, 1);
}
