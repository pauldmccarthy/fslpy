/*
 * OpenGL fragment shader used by fsl/fslview/gl/gl21/glvolume_funcs.py.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

#pragma include spline_interp.glsl

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
 * Transformation from display space to voxel coordinates.
 */
uniform mat4 displayToVoxMat;

/*
 * Transformation matrix to apply to the 1D texture coordinate.
 */
uniform mat4 voxValXform;

/*
 * Image texture coordinates. 
 */
varying vec3 fragTexCoords;


void main(void) {

    /*
     * Transform the texture coordinates into voxel coordinates
     */
    vec4 voxCoords = displayToVoxMat * vec4(fragTexCoords, 1);

    /*
     * Centre voxel coordinates
     */
    voxCoords.xyz = voxCoords.xyz + 0.5;

    /*
     * Don't render the fragment if it's outside the image space
     */
    if (voxCoords.x < -0.01 || voxCoords.x >= imageShape.x + 0.01 ||
        voxCoords.y < -0.01 || voxCoords.y >= imageShape.y + 0.01 ||
        voxCoords.z < -0.01 || voxCoords.z >= imageShape.z + 0.01) {
        
        gl_FragColor = vec4(0.0, 0.0, 0.0, 0.0);
        return;
    }

    /*
     * Be lenient at voxel boundaries
     */
    if (voxCoords.x <  0.0)          voxCoords.x = 0.01;
    if (voxCoords.y <  0.0)          voxCoords.y = 0.01;
    if (voxCoords.z <  0.0)          voxCoords.z = 0.01; 
    if (voxCoords.x >= imageShape.x) voxCoords.x = imageShape.x - 0.01;
    if (voxCoords.y >= imageShape.y) voxCoords.y = imageShape.y - 0.01;
    if (voxCoords.z >= imageShape.z) voxCoords.z = imageShape.z - 0.01;

    /* 
     * Normalise voxel coordinates to (0.0, 1.0)
     */
    voxCoords.xyz = voxCoords.xyz / imageShape.xyz;

    /*
     * Look up the voxel value 
     */
    float voxValue;
    if (useSpline) voxValue = spline_interp(imageTexture,
                                            voxCoords.xyz,
                                            imageShape,
                                            0);
    else           voxValue = texture3D(    imageTexture,
                                            voxCoords.xyz).r;

    /*
     * Transform the voxel value to a colour map texture
     * coordinate, and look up the colour for the voxel value
     */
    vec4 normVoxValue = voxValXform * vec4(voxValue, 0, 0, 1);
    gl_FragColor      = texture1D(colourTexture, normVoxValue.x); 
}
