/*
 * OpenGL vertex shader used for rendering GLObject instances.
 *
 * All this shader does is transfer texture coordinates through
 * to the fragment shader.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120


uniform mat4 displayToVoxMat;

/*
 * Optional transformation matrix which is applied to all
 * vertex coordinates (used by the e.g. lightbox canvas to
 * organise individual slices in a row/column fashion).
 */
uniform mat4 worldToWorldMat;

/*
 * Display axes (xax = horizontal, yax = vertical, zax = depth)
 */
uniform int xax;
uniform int yax;
uniform int zax;

/*
 * X/Y vertex location
 */
attribute vec2 worldCoords;

/*
 * Z location
 */
uniform float zCoord;

/* 
 * Image texture coordinates passed through to fragment shader.
 */ 
varying vec3 fragTexCoords;


/* 
 * Image voxel coordinates corresponding to this vertex.
 */ 
varying vec3 fragVoxCoords;


void main(void) {

    vec4 worldLoc = vec4(0, 0, 0, 1);
    worldLoc[xax] = worldCoords.x;
    worldLoc[yax] = worldCoords.y;
    worldLoc[zax] = zCoord;

    /*
     * Transform the texture coordinates into voxel coordinates
     */
    fragVoxCoords = (displayToVoxMat * worldLoc).xyz;

    /*
     * Centre voxel coordinates - the display space of a voxel
     * at a particular location (x, y, z) extends from
     *
     * (x-0.5, y-0.5, z-0.5)
     *
     * to
     *
     * (x+0.5, y+0.5, z+0.5),
     *
     * so we need to offset the coordinates by 0.5 to
     * make the coordinates usable as voxel indices
     */
    fragVoxCoords.xyz = fragVoxCoords.xyz + 0.5;

    /*
     * Pass the vertex coordinates as texture
     * coordinates to the fragment shader
     */
    fragTexCoords = worldLoc.xyz; 

    /* Transform the vertex coordinates to display space */
    gl_Position = gl_ModelViewProjectionMatrix * worldToWorldMat * worldLoc;
}
