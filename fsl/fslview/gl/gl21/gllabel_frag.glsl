#version 120

#pragma include spline_interp.glsl
#pragma include test_in_bounds.glsl

uniform sampler3D imageTexture;

uniform sampler1D lutTexture;

uniform mat4      voxValXform;

uniform vec3      imageShape;

uniform float     numLabels;

uniform bool      useSpline;

uniform bool      outline;

uniform float     outlineOffsets[3];

varying vec3      fragVoxCoord;

varying vec3      fragTexCoord;


void main(void) {

    vec3 voxCoord = fragVoxCoord;

    if (!test_in_bounds(voxCoord, imageShape)) {
        
        gl_FragColor = vec4(0, 0, 0, 0);
        return;
    }

    float voxValue;
    voxValue = texture3D(imageTexture, fragTexCoord).r;

    float lutCoord = ((voxValXform * vec4(voxValue, 0, 0, 1)).x + 0.5) / numLabels;

    if (lutCoord < 0 || lutCoord > 1) {
        gl_FragColor.a = 0.0;
        return;
    }
    
    vec4 colour = texture1D(lutTexture, lutCoord);

    if (!outline || colour.a == 0) {
      gl_FragColor = colour;
    }
    else {

        float tol = 0.01 / numLabels;
        vec3  off;
        
        for (int i = 0; i < outlineOffsets.length(); i++) {

            if (outlineOffsets[i] <= 0)
                continue;

            off    = vec3(0, 0, 0);
            off[i] = outlineOffsets[i];

            float back  = texture3D(imageTexture, fragTexCoord + off).r;
            float front = texture3D(imageTexture, fragTexCoord - off).r;

            if (abs(voxValue - back)  > tol ||
                abs(voxValue - front) > tol) {
                gl_FragColor = colour;
                return;
            }
        }

        gl_FragColor.a = 0.0;
    }
}
