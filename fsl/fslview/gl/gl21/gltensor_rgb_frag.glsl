/*
 * OpenGL fragment shader used by fsl/fslview/gl/gl21/slicecanvas_draw.py.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

#pragma include spline_interp.glsl

/*
 * image data texture
 */
uniform sampler3D imageTexture;


uniform sampler3D modTexture;

uniform sampler1D xColourTexture;
uniform sampler1D yColourTexture;
uniform sampler1D zColourTexture;

/*
 * Image/texture dimensions
 */
uniform vec3 imageShape;

/*
 * Use spline interpolation?
 */
uniform bool useSpline;

/*
 * Transformation from display space to voxel coordinates.
 */
uniform mat4 displayToVoxMat;

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
     * Look up the xyz tensor values
     */
    vec3 voxValue;
    if (useSpline) {
       voxValue.x = spline_interp(imageTexture, voxCoords.xyz, imageShape, 0);
       voxValue.y = spline_interp(imageTexture, voxCoords.xyz, imageShape, 1);
       voxValue.z = spline_interp(imageTexture, voxCoords.xyz, imageShape, 2);
    }
    else {
        voxValue = texture3D(imageTexture, voxCoords.xyz).xyz;
    }

    /* Look up the modulation value */
    vec3 modValue;
    if (useSpline) {
        float tmp = spline_interp(modTexture, voxCoords.xyz, imageShape, 0);
        modValue.xyz = vec3(tmp, tmp, tmp);
    }
    else {
        modValue = texture3D(modTexture, voxCoords.xyz).xxx;
    }

    /* Look up the colours for the xyz components */
    vec4 xColour = texture1D(xColourTexture, voxValue.x);
    vec4 yColour = texture1D(yColourTexture, voxValue.y);
    vec4 zColour = texture1D(zColourTexture, voxValue.z);

    /* Combine those colours */
    vec4 voxColour = xColour + yColour + zColour;

    /* Apply the modulation value and average the transparency */
    voxColour.xyz = voxColour.xyz * modValue;
    voxColour.a   = voxColour.a   / 0.333333;

    gl_FragColor = voxColour;
}
