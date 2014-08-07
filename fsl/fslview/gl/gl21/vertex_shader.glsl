/*
 * OpenGL vertex shader used by fsl/fslview/slicecanvas.py
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

/* image data texture */
uniform sampler3D imageBuffer;

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


attribute vec2 texCoords;

/* Z location*/
uniform float zCoord;

/* Voxel value passed through to fragment shader */ 
varying float fragVoxValue;

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

    vec4 voxLoc = worldToVoxMat * texLoc;
    voxLoc      = (voxLoc + 0.5) / vec4(imageShape, 1.0);

    /* Look up the voxel value, and pass it to the fragment shader */
    vec4 vt = texture3D(imageBuffer, voxLoc.xyz);
    fragVoxValue = vt.r;
}
