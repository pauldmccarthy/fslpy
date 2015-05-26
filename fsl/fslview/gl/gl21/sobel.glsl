/*
 *
 */
vec4 sobel(sampler2D tex, float width, float height, vec2 coord) {

  vec4 s1 = texture2D(tex, coord + vec2(-1.0 / width, -1.0 / height));
  vec4 s2 = texture2D(tex, coord + vec2( 1.0 / width, -1.0 / height));
  vec4 s3 = texture2D(tex, coord + vec2(-1.0 / width,  1.0 / height));
  vec4 s4 = texture2D(tex, coord + vec2( 1.0 / width,  1.0 / height));
  
  vec4 sx = 4.0 * ((s4 + s3) - (s2 + s1));
  vec4 sy = 4.0 * ((s2 + s4) - (s1 + s3));
  vec4 result = sqrt(sx * sx + sy * sy);
  
  return result;
}




