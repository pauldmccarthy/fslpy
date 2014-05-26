/*
 * OpenGL vertex shader used by fsl/fslview/slicecanvas.py
 *
 * Author: Paul McCarthy <pauldmccarthy@gmail.com>
 */
#version 120

/* Opacity - constant for a whole image */
uniform float alpha;

uniform float sampleRate;

/* image data texture */
uniform sampler3D dataBuffer;

/* Voxel coordinate -> world space transformation matrix */
uniform mat4 voxToWorldMat;

/* Image dimensions */
uniform float xdim;
uniform float ydim;
uniform float zdim;

/* Current vertex */
attribute vec3 inVertex;

/* Current voxel coordinates */
attribute float voxX;
attribute float voxY;
attribute float voxZ;

/* Voxel value passed through to fragment shader */ 
varying float fragVoxValue;

void main(void) {

    vec3 vertPos = inVertex * sampleRate;

    /*
     * Offset the vertex by the current voxel position
     * (and perform standard transformation from data
     * coordinates to screen coordinates).
     */
    vertPos = vertPos + vec3(voxX, voxY, voxZ);
    gl_Position = gl_ModelViewProjectionMatrix * 
        (voxToWorldMat * vec4(vertPos, 1.0));

    /* Pass the voxel value through to the shader. */
    float normVoxX = voxX / xdim + 0.5 / xdim;
    float normVoxY = voxY / ydim + 0.5 / ydim;
    float normVoxZ = voxZ / zdim + 0.5 / zdim;
    vec4 vt = texture3D(dataBuffer, vec3(normVoxX, normVoxY, normVoxZ));
    fragVoxValue = vt.r;
}
