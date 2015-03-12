/*
 * OpenGL vertex shader used for rendering GLVector instances in
 * line mode.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

#pragma include common_vert.glsl
#pragma include spline_interp.glsl

/*
 * Vector image containing XYZ vector data.
 */
uniform sampler3D imageTexture;


/*
 * Transformation matrix which transforms the
 * vector texture data to its original data range.
 */
uniform mat4 imageValueXform;


/*
 * Matrix which transforms from voxel
 * coordinates to display coordinates.
 */
uniform mat4 voxToDisplayMat;

/*
 * Shape of the image texture.
 */
uniform vec3 imageShape;

/*
 * Dimensions of one voxel in the image texture.
 */
uniform vec3 imageDims;

/*
 * Vertex index - the built-in gl_VertexID
 * variable is not available in GLSL 120
 */
attribute float vertexID;


void main(void) {

  common_vert();

  vec3 voxCoords = fragVoxCoords;
  vec3 vertexPos = fragVoxCoords - 0.5;
  vec3 vector;

  /*
   * Normalise the vertex coordinates to [0.0, 1.0],
   * so they can be used for texture lookup. And make
   * sure the voxel coordinates are exact integers 
   * (actually, that they are centred within the
   * voxel - see common_vert.glsl), as we cannot
   * interpolate vector directions.
   */
  voxCoords = (floor(voxCoords) + 0.5) / imageShape;

  /*
   * Retrieve the vector values for this voxel
   */
  vector = texture3D(imageTexture, voxCoords).xyz;

  /*
   * Transform the vector values  from their
   * texture range of [0,1] to the original
   * data range
   */
  vector *= imageValueXform[0].x;
  vector += imageValueXform[0].w;

  vector *= 0.5;

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
  vertexPos += vector;

  /*
   * Output the final vertex position
   */
  gl_Position = gl_ModelViewProjectionMatrix * 
                worldToWorldMat * 
                voxToDisplayMat * 
                vec4(vertexPos, 1);
}
