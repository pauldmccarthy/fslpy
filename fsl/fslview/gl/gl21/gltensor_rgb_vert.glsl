/*
 * OpenGL vertex shader used by fsl/fslview/gl/gl21/gltensor_rgb_funcs.py.
 *
 * All this shader does is transfer texture coordinates through
 * to the fragment shader.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

/*
 * Optional transformation matrix which is applied to all
 * vertex coordinates.
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


void main(void) {

    vec4 worldLoc = vec4(0, 0, 0, 1);
    worldLoc[xax] = worldCoords.x;
    worldLoc[yax] = worldCoords.y;
    worldLoc[zax] = zCoord;

    /*
     * Pass the vertex coordinates as texture
     * coordinates to the fragment shader
     */
    fragTexCoords = worldLoc.xyz; 

    /* Transform the vertex coordinates to display space */
    gl_Position = gl_ModelViewProjectionMatrix * worldToWorldMat * worldLoc;
}
