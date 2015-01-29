/**
 * The common_vert function (and associated uniform/attribute/varying
 * definitions) contains logic which is common to all vertex shader
 * programs.
 *
 * The common_vert function calculates and sets vertex/texture
 * coordinates, for pass-through to the fragment shader, in both
 * screen space and voxel space.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */

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
 * Vertex display coordinates passed through to fragment shader.
 */ 
varying vec3 fragDisplayCoords;

/* 
 * Image voxel coordinates corresponding to this vertex.
 */ 
varying vec3 fragVoxCoords;


void common_vert(void) {

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
    fragVoxCoords += 0.5;

    /*
     * Pass the vertex coordinates as texture
     * coordinates to the fragment shader
     */
    fragDisplayCoords = worldLoc.xyz; 

    /* Transform the vertex coordinates to display space */
    gl_Position = gl_ModelViewProjectionMatrix * worldToWorldMat * worldLoc;
}
