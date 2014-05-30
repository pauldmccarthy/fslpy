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
 * Does the voxel value need to be normalised by the image
 * range? 
 */
uniform bool needNorm;

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

    float normVoxValue;

    if (needNorm) normVoxValue = (fragVoxValue - dataMin) / (dataMax - dataMin);
    else          normVoxValue = fragVoxValue;

    vec4  voxTexture = texture1D(colourMap, normVoxValue);  
    vec3  voxColour  = voxTexture.rgb;
    float voxAlpha   = alpha;

    if (voxTexture.a < voxAlpha) voxAlpha = voxTexture.a;

    gl_FragColor = vec4(voxColour, voxAlpha);
}