/*
 * OpenGL fragment shader used for colouring GLVector instances in
 * both line and rgb modes.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

#pragma include spline_interp.glsl
#pragma include test_in_bounds.glsl

/*
 * Vector image containing XYZ vector data.
 */
uniform sampler3D imageTexture;

/*
 * Modulation texture containing values by
 * which the vector colours are to be modulated.
 */
uniform sampler3D modTexture;

/*
 * If the modulation value is below this
 * threshold, the fragment is made
 * transparent.
 */
uniform float modThreshold;

/*
 * Colour map for the X vector component.
 */
uniform sampler1D xColourTexture;

/*
 * Colour map for the Y vector component.
 */
uniform sampler1D yColourTexture;

/*
 * Colour map for the Z vector component.
 */
uniform sampler1D zColourTexture;

/*
 * Matrix which transforms from vector image
 * texture values to their original data range.
 */
uniform mat4 imageValueXform;


uniform mat4 colourMapXform;

/*
 * Shape of the image texture.
 */
uniform vec3 imageShape;

/*
 * Use spline interpolation?
 */
uniform bool useSpline;


/*
 * Coordinates of the fragment in display
 * coordinates, passed from the vertex shader.
 */
varying vec3 fragDisplayCoords;

/*
 * Coordinates of the fragment in voxel
 * coordinates, passed from the vertex shader.
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
   * into a range suitable for colour texture
   * lookup, and take the absolute value
   */
  voxValue  = abs(voxValue);
  voxValue *= colourMapXform[0].x;
  voxValue += colourMapXform[3].x;

  /* Look up the modulation value */
  float modValue;
  if (useSpline) {
    modValue = spline_interp(modTexture, voxCoords, imageShape, 0);
  }
  else {
    modValue = texture3D(modTexture, voxCoords).x;
  }

  /* Look up the colours for the xyz components */
  vec4 xColour = texture1D(xColourTexture, voxValue.x);
  vec4 yColour = texture1D(yColourTexture, voxValue.y);
  vec4 zColour = texture1D(zColourTexture, voxValue.z);

  /* Combine those colours */
  vec4 voxColour = xColour + yColour + zColour;

  /* Apply the modulation value */
  voxColour.rgb = voxColour.rgb * modValue;
  voxColour.a   = max(max(xColour.a, yColour.a), zColour.a);

  if (modValue < modThreshold)
    voxColour.a = 0.0;

  gl_FragColor = voxColour;
}
