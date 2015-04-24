/*
 * OpenGL vertex shader used for rendering GLVector instances in
 * line mode.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

#pragma include spline_interp.glsl

/*
 * Vector image containing XYZ vector data.
 */
uniform sampler3D imageTexture;


uniform mat4 displayToVoxMat;
uniform mat4 voxToDisplayMat;


/*
 * Transformation matrix which transforms the
 * vector texture data to its original data range.
 */
uniform mat4 voxValXform;


/*
 * Shape of the image texture.
 */
uniform vec3 imageShape;


uniform bool directed;

/*
 * Dimensions of one voxel in the image texture.
 */
uniform vec3 imageDims;


attribute vec3 vertex;

/*
 * Vertex index - the built-in gl_VertexID
 * variable is not available in GLSL 120
 */
attribute float vertexID;


varying vec3 fragVoxCoord;
varying vec3 fragTexCoord;


void main(void) {

  vec3 vertexPos;
  vec3 texCoord;
  vec3 vector;

  vec3 voxCoord = (displayToVoxMat * vec4(vertex, 0)).xyz + 0.5;
  
  /*
   * Normalise the vertex coordinates to [0.0, 1.0],
   * so they can be used for texture lookup. And make
   * sure the voxel coordinates are exact integers 
   * (actually, that they are centred within the
   * voxel, as we cannot interpolate vector directions.
   */
  texCoord = floor(voxCoord + 0.5) / imageShape;

  /*
   * Retrieve the vector values for this voxel
   */
  vector = texture3D(imageTexture, texCoord).xyz;

  /*
   * Transform the vector values  from their
   * texture range of [0,1] to the original
   * data range
   */
  vector *= voxValXform[0].x;
  vector += voxValXform[3].x;

  // Scale the vector so it has length 0.5 
  vector /= 2 * length(vector);

  /*
   * Vertices are coming in as line pairs - flip
   * every second vertex about the origin
   */
  if (mod(vertexID, 2) == 1) {
    if (directed) vector = vec3(0, 0, 0);
    else          vector = -vector;
  }

  /*
   * Scale the vector by the minimum voxel length,
   * so it is a unit vector within real world space 
   */
  vector /= imageDims / min(imageDims.x, min(imageDims.y, imageDims.z));

  vec3 v = vertex;

  if (mod(vertexID, 2) == 1) v += vec3(0.5, 0.5, 0.5);
  else                       v += vec3(0,   0,   0);
  
  /*
   * Output the final vertex position
   */
  gl_Position = gl_ModelViewProjectionMatrix *
                voxToDisplayMat              *
                vec4(v, 1);

  fragVoxCoord = voxCoord;
  fragTexCoord = texCoord;
}
