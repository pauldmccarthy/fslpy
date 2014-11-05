/*
 * OpenGL vertex shader used by fsl/fslview/gl/gl21/slicecanvas_draw.py.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120
#extension GL_EXT_gpu_shader4 : require

/* World coordinate -> voxel coordinate transformation matrix */
uniform mat4 worldToVoxMat;
uniform mat4 worldToWorldMat;

uniform int xax;
uniform int yax;
uniform int zax;
uniform int samplingRate;

/* Image dimensions */
uniform vec3 imageShape;

/* X/Y world location */
attribute vec2 worldCoords;

/* Texture coordinate used to look up the voxel value for this vertex */
attribute vec2 texCoords;

/* Z location*/
uniform float zCoord;

/* 
 * Image texture coordinates passed through to fragment shader.
 */ 
flat varying vec3 fragTexCoords;

/* 
 * If the world location is out of bounds, tell 
 * the fragment shader not to draw the fragment. 
 */
varying float outOfBounds;


void main(void) {

    vec4 worldLoc = vec4(0, 0, 0, 1);
    vec4 texLoc   = vec4(0, 0, 0, 1);
    worldLoc[xax] = worldCoords.x;
    worldLoc[yax] = worldCoords.y;
    worldLoc[zax] = zCoord;
    texLoc[  xax] = texCoords.x;
    texLoc[  yax] = texCoords.y;
    texLoc[  zax] = zCoord; 

    worldLoc    = gl_ModelViewProjectionMatrix * worldToWorldMat * worldLoc;
    gl_Position = worldLoc;

    /* transform the texture world coordinate into voxel coordinates */
    vec4 voxLoc = worldToVoxMat * texLoc;

    /*
     * Figure out whether we are out of the image space.        
     * Be a bit lenient at the voxel coordinate boundaries, 
     * as otherwise the 3D texture lookup will be out of 
     * bounds.
     */
    outOfBounds = 0;

    if      (voxLoc.x < -0.5)                  outOfBounds = 1;
    else if (voxLoc.x >  imageShape.x - 0.499) outOfBounds = 1;
    else if (voxLoc.x >= imageShape.x - 0.5)   voxLoc.x = imageShape.x - 0.501;
    if      (voxLoc.y < -0.5)                  outOfBounds = 1;
    else if (voxLoc.y >  imageShape.y - 0.499) outOfBounds = 1;
    else if (voxLoc.y >= imageShape.y - 0.5)   voxLoc.y = imageShape.y - 0.501;
    if      (voxLoc.z < -0.5)                  outOfBounds = 1;
    else if (voxLoc.z >  imageShape.z - 0.499) outOfBounds = 1;
    else if (voxLoc.z >= imageShape.z - 0.5)   voxLoc.z = imageShape.z - 0.501;

    /* Pass the texture coordinates to the fragment shader */
    fragTexCoords = (voxLoc.xyz + 0.5) / imageShape;
}
