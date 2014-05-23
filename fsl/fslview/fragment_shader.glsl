/*
 * OpenGL fragment shader used by fsl/fslview/slicecanvas.py
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

uniform float     alpha;
uniform sampler1D colourMap;
varying float     fragVoxValue;

void main(void) {

    vec4  voxTexture = texture1D(colourMap, fragVoxValue);
    vec3  voxColour  = voxTexture.rgb;
    float voxAlpha   = alpha;

    if (voxTexture.a < voxAlpha) voxAlpha = voxTexture.a;

    gl_FragColor = vec4(voxColour, voxAlpha);
}