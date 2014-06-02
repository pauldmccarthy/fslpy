/*
 * OpenGL fragment shader used by fsl/fslview/slicecanvas.py
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

/* 
 * image opacity (will be overridden by the opacity in the 
 * colour map, if it is lower) 
 */
uniform float alpha;

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


/*
 * The voxel value is multiplied and offset  by these 
 * values to  map it into texture coordinates.
 */
uniform float normFactor;
uniform float normOffset;

/*
 * Maximum/minimum image values.
 */
uniform float dataMin;
uniform float dataMax;

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

    normVoxValue = (normVoxValue - normOffset) * normFactor;

    vec4  voxTexture = texture1D(colourMap, normVoxValue);  
    vec3  voxColour  = voxTexture.rgb;
    float voxAlpha   = alpha;

    if (voxTexture.a < voxAlpha) voxAlpha = voxTexture.a;

    gl_FragColor = vec4(voxColour, voxAlpha);
}