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

varying vec3      fragVoxCoord;

varying vec3      fragTexCoord;


void main(void) {

    vec3 voxCoord = fragVoxCoord;

    if (!test_in_bounds(voxCoord, imageShape)) {
        
        gl_FragColor = vec4(0, 0, 0, 0);
        return;
    }

    float voxValue;
    if (useSpline) voxValue = spline_interp(imageTexture,
                                            fragTexCoord,
                                            imageShape,
                                            0);
    else           voxValue = texture3D(    imageTexture,
                                            fragTexCoord).r;

    float lutCoord = (voxValXform * vec4(voxValue, 0, 0, 1)).x / numLabels;
    vec4 colour    = texture1D(lutTexture, lutCoord);

    if (outline) {

        // TODO take into account resolution
        vec3 off = 0.1 / imageShape;

        float left   = texture3D(imageTexture,
                                 fragTexCoord + vec3(-off.x, 0,      0))    .r;
        float right  = texture3D(imageTexture,
                                 fragTexCoord + vec3( off.x, 0,      0))    .r;
        float top    = texture3D(imageTexture,
                                 fragTexCoord + vec3( 0,     off.y,  0))    .r;
        float bottom = texture3D(imageTexture,
                                 fragTexCoord + vec3( 0,    -off.y,  0))    .r;
        float back   = texture3D(imageTexture,
                                 fragTexCoord + vec3( 0,     0,     -off.z)).r;
        float front  = texture3D(imageTexture,
                                 fragTexCoord + vec3( 0,     0,      off.z)).r;


        voxValue = (voxValXform * vec4(voxValue, 0, 0, 1)).x;
        left     = (voxValXform * vec4(left,     0, 0, 1)).x;
        right    = (voxValXform * vec4(right,    0, 0, 1)).x;
        top      = (voxValXform * vec4(top,      0, 0, 1)).x;
        bottom   = (voxValXform * vec4(bottom,   0, 0, 1)).x;
        back     = (voxValXform * vec4(back,     0, 0, 1)).x;
        front    = (voxValXform * vec4(front,    0, 0, 1)).x;

        if (abs(voxValue - top)    < 0.001 &&
            abs(voxValue - bottom) < 0.001 &&
            abs(voxValue - left)   < 0.001 &&
            abs(voxValue - right)  < 0.001 &&
            abs(voxValue - back)   < 0.001 &&
            abs(voxValue - front)  < 0.001)
          colour.a = 0.0;
    }

    gl_FragColor = colour;
}
