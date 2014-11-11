/*
 * OpenGL fragment shader used by fsl/fslview/gl/gl21/slicecanvas_draw.py.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

#pragma include spline_interp.glsl

/* image data texture */
uniform sampler3D imageBuffer;

/* Image/texture dimensions */
uniform vec3 imageShape;

/*
 * Texture containing the colour map
 */
uniform sampler1D colourMap;

/*
 * Use spline interpolation?
 */
uniform bool useSpline;

/*
 * Transformation matrix to apply to the 1D texture coordinate.
 */
uniform mat4 texCoordXform;

/*
 * Image texture coordinates. 
 */
varying vec3 fragTexCoords;

/*
 * If non-zero, the fragment is not drawn.
 */
varying float outOfBounds;

void main(void) {

    if (outOfBounds > 0) {
      gl_FragColor = vec4(0, 0, 0, 0);
      return;
    }

    float normVoxValue;

    if (useSpline) normVoxValue = spline_interp(imageBuffer,
                                                fragTexCoords,
                                                imageShape);
    else           normVoxValue = texture3D(    imageBuffer,
                                                fragTexCoords).r;

    vec4 texCoord = texCoordXform * vec4(normVoxValue, 0, 0, 1);
    gl_FragColor  = texture1D(colourMap, texCoord.x); 
}