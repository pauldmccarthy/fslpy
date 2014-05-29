/*
 * OpenGL vertex shader used by fsl/fslview/slicecanvas.py
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

/* Opacity - constant for a whole image */
uniform float alpha;

/* image data texture */
uniform sampler3D imageBuffer;

/* Voxel coordinate -> world space transformation matrix */
uniform mat4 voxToWorldMat;

/* Image dimensions */
uniform vec3 imageShape;

/* Image texture dimensions */
uniform vec3 fullTexShape;
uniform vec3 subTexShape;
uniform vec3 subTexPad;

/* Current vertex */
attribute vec3 inVertex;

/* Current voxel coordinates */
attribute float voxX;
attribute float voxY;
attribute float voxZ;

/* Voxel value passed through to fragment shader */ 
varying float fragVoxValue;

void main(void) {

    vec3 vox = vec3(voxX, voxY, voxZ);  

    /*
     * Offset the vertex by the current voxel position
     * (and perform standard transformation from data
     * coordinates to screen coordinates).
     */
    gl_Position = gl_ModelViewProjectionMatrix * 
        (voxToWorldMat * vec4(inVertex + vox, 1.0));

    /* Transform from voxel coordinates to sub-texture coordinates */
    vox = ((vox + 0.5) / imageShape) * (subTexShape - subTexPad);

    /* And then transform from sub-texture coords to normalised 
       full-texture coordinates */
    vox = vox / fullTexShape;

    vec4 vt = texture3D(imageBuffer, vox);
    fragVoxValue = vt.r;
}
