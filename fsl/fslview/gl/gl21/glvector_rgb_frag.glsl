/*
 * OpenGL fragment shader used for colouring GLVector instances.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

#pragma include spline_interp.glsl

#pragma include test_in_bounds.glsl

/*
 * image data texture
 */
uniform sampler3D imageTexture;


uniform sampler3D modTexture;

uniform sampler1D xColourTexture;
uniform sampler1D yColourTexture;
uniform sampler1D zColourTexture;

uniform mat4 imageValueXform;

/*
 * Image/texture dimensions
 */
uniform vec3 imageShape;

/*
 * Use spline interpolation?
 */
uniform bool useSpline;

/*
 * Image display coordinates. 
 */
varying vec3 fragDisplayCoords;

/*
 * Image voxel coordinates
 */
varying vec3 fragVoxCoords;

void main(void) {

    vec3 voxCoords = fragVoxCoords;

    if (!test_in_bounds(voxCoords, imageShape)) {

        gl_FragColor = vec4(0.0, 0.0, 0.0, 0.0);
        return;
    }

    /* 
     * Normalise voxel coordinates to (0.0, 1.0)
     */
    voxCoords = voxCoords / imageShape;

    /*
     * Look up the xyz vector values
     */
    vec3 voxValue;
    if (useSpline) {
       voxValue.x = spline_interp(imageTexture, voxCoords, imageShape, 0);
       voxValue.y = spline_interp(imageTexture, voxCoords, imageShape, 1);
       voxValue.z = spline_interp(imageTexture, voxCoords, imageShape, 2);
    }
    else {
        voxValue = texture3D(imageTexture, voxCoords).xyz;
    }

    /*
     * Transform the voxel texture values 
     * into their original range
     */
    voxValue *= imageValueXform[0].x;
    voxValue += imageValueXform[0].w;
    voxValue  = abs(voxValue);

    /* Look up the modulation value */
    vec3 modValue;
    if (useSpline) {
        float tmp = spline_interp(modTexture, voxCoords, imageShape, 0);
        modValue.xyz = vec3(tmp, tmp, tmp);
    }
    else {
        modValue = texture3D(modTexture, voxCoords).xxx;
    }

    /* Look up the colours for the xyz components */
    vec4 xColour = texture1D(xColourTexture, voxValue.x);
    vec4 yColour = texture1D(yColourTexture, voxValue.y);
    vec4 zColour = texture1D(zColourTexture, voxValue.z);

    /* Combine those colours */
    vec4 voxColour = xColour + yColour + zColour;

    /* Apply the modulation value and average the transparency */
    voxColour.xyz = voxColour.xyz * modValue;
    voxColour.a   = voxColour.a   * 0.333333;

    gl_FragColor = voxColour;
}
