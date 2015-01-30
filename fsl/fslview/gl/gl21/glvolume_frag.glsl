/*
 * OpenGL fragment shader used by fsl/fslview/gl/gl21/glvolume_funcs.py.
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

/*
 * Image/texture dimensions
 */
uniform vec3 imageShape;

/*
 * Texture containing the colour map
 */
uniform sampler1D colourTexture;

/*
 * Use spline interpolation?
 */
uniform bool useSpline;

/*
 * Transformation matrix to apply to the 1D texture coordinate.
 */
uniform mat4 voxValXform;

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
     * Look up the voxel value 
     */
    float voxValue;
    if (useSpline) voxValue = spline_interp(imageTexture,
                                            voxCoords,
                                            imageShape,
                                            0);
    else           voxValue = texture3D(    imageTexture,
                                            voxCoords).r;

    /*
     * Transform the voxel value to a colour map texture
     * coordinate, and look up the colour for the voxel value
     */
    vec4 normVoxValue = voxValXform * vec4(voxValue, 0, 0, 1);
    gl_FragColor      = texture1D(colourTexture, normVoxValue.x); 
}
