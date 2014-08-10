/*
 * OpenGL fragment shader used by fsl/fslview/slicecanvas.py
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

/*
 * Texture containing the colour map
 */
uniform sampler1D colourMap;

/*
 * If the voxel value is a signed integer, OpenGL maps
 * positive values to [0, 0.5], and negative values to 
 * [0.5, 1.0]. If this flag is true, signed integers
 * are handled correctly.
 */
uniform bool signed;

uniform mat4 texCoordXform;

/*
 * Voxel value - Might be unnormalised, or normalised to lie
 * in the range [0,1].
 */
varying float fragVoxValue;

void main(void) {

    float normVoxValue = fragVoxValue;

    if (signed) {
        if (normVoxValue >= 0.5) normVoxValue = normVoxValue - 0.5;
        else                     normVoxValue = normVoxValue + 0.5;
    }   

    vec4 texCoord = texCoordXform * vec4(normVoxValue, 0, 0, 1);
    gl_FragColor  = texture1D(colourMap, texCoord.x); 
}