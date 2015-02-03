/*
 * Provides the briconalpha function, which applies global brightness,
 * contrast and alpha settings to a specified colour.
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */

/*
 * Brightness factor, assumed to lie between 0.0 and 1.0.
 */
uniform float brightness;

/*
 * Contrast factor, assumed to lie between 0.0 and 1.0.
 */
uniform float contrast;

/*
 * Opacity, assumed to lie between 0.0 and 1.0.
 */
uniform float alpha;


vec4 briconalpha(vec4 inputColour) {

  float scale;
  float offset;
  vec4  outputColour = vec4(inputColour);

  if (outputColour.a >= 1.0)
    outputColour.a = alpha;

  /*
   * The brightness is applied as a linear offset,
   * with 0.5 equivalent to an offset of 0.0.
   */
  offset = (brightness * 2 - 1);

  /*
   * If the contrast lies between 0.0 and 0.5, it is
   * applied to the colour as a linear scaling factor.
   */
  scale = contrast * 2;

  /*
   * If the contrast lies between 0.5 and 0.1, it
   * is applied as an exponential scaling factor,
   * so lower values (closer to 0.5) have less of
   * an effect than higher values (closer to 1.0).
   */
  if (contrast > 0.5) 
    scale += exp((contrast - 0.5) * 6) - 1;

  /*
   * The contrast factor scales the existing colour
   * range, but keeps the new range centred at 0.5.
   */
  outputColour.rgb += offset;
  
  outputColour.rgb  = clamp(outputColour.rgb, 0.0, 1.0);
  outputColour.rgb  = (outputColour.rgb - 0.5) * scale + 0.5;
    
  return clamp(outputColour, 0.0, 1.0);
}
