/*
 * OpenGL fragment shader used by fsl/fslview/gl/gl21/slicecanvas_draw.py.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

/* image data texture */
uniform sampler3D imageBuffer;

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

    float normVoxValue = texture3D(imageBuffer, fragTexCoords).r;

    if (signed) {
        if (normVoxValue >= 0.5) normVoxValue = normVoxValue - 0.5;
        else                     normVoxValue = normVoxValue + 0.5;
    }   

    vec4 texCoord = texCoordXform * vec4(normVoxValue, 0, 0, 1);
    gl_FragColor  = texture1D(colourMap, texCoord.x); 
}