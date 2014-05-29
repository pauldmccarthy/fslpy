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
    vec3 vertPos = inVertex + vox;
    gl_Position = gl_ModelViewProjectionMatrix * 
        (voxToWorldMat * vec4(vertPos, 1.0));

    /* Pass the voxel value through to the shader. */
    vec3 normVox = (vox + 0.5) / imageShape;

    vec4 vt = texture3D(imageBuffer, normVox);
    fragVoxValue = vt.r;
}
