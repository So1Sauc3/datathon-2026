// CRT emulation from Hammster/windows-terminal-shaders (crt.hlsl), CC0.
// An overlay cannot sample the page beneath it, so the passes that read the
// screen (overscan, bloom, blur, grayscale, tint) are left out and the curve
// only masks the glass edge instead of warping content. The rest are output
// as premultiplied alpha: darkening raises alpha, grain adds light.

export const crtFragment = /* glsl */ `
uniform float uTime;
uniform vec2 uResolution;
uniform float uScale;

#define CURVE_INTENSITY 0.3
#define SCANLINE_FACTOR 0.3
#define GRAIN_INTENSITY 0.02

vec2 transformCurve(vec2 uv) {
  uv -= 0.5;
  float r = (uv.x * uv.x + uv.y * uv.y) * CURVE_INTENSITY;
  uv *= 4.0 + r;
  uv *= 0.25;
  return uv + 0.5;
}

float refreshLine(vec2 uv) {
  float timeOver = mod(uTime / 5.0, 1.5) - 0.5;
  if (uv.y > timeOver && uv.y - 0.03 < timeOver) return (uv.y - timeOver) * 2.0;
  return 0.0;
}

float scanline(float y) {
  return 1.0 - mod(floor(y / uScale), 2.0) * SCANLINE_FACTOR;
}

#define a0  0.151015505647689
#define a1 -0.5303572634357367
#define a2  1.365020122861334
#define b0  0.132089632343748
#define b1 -0.7607324991323768

float permute(float x) {
  x *= 34.0 * x + 1.0;
  return 289.0 * fract(x / 289.0);
}

float rand(inout float state) {
  state = permute(state);
  return fract(state / 41.0);
}

float grain(vec2 uv) {
  vec3 m = vec3(uv, mod(uTime, 5.0) / 5.0) + 1.0;
  float state = permute(permute(m.x) + m.y) + m.z;
  float p = 0.95 * rand(state) + 0.025;
  float q = p - 0.5;
  float r2 = q * q;
  return GRAIN_INTENSITY * q * (a2 + (a1 * r2 + a0) / (r2 * r2 + b1 * r2 + b0));
}

void main() {
  vec2 uv = gl_FragCoord.xy / uResolution;
  uv.y = 1.0 - uv.y;

  vec2 glass = transformCurve(uv);
  vec2 edge = max(-glass, glass - 1.0);
  float outside = max(edge.x, edge.y);
  if (outside > 0.025) { gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0); return; }
  if (outside > 0.015) { gl_FragColor = vec4(0.03, 0.03, 0.03, 1.0); return; }
  if (outside > 0.001) { gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0); return; }

  float shade = (1.0 - refreshLine(glass)) * scanline(gl_FragCoord.y);
  float g = grain(glass);
  float light = max(g, 0.0);
  float alpha = clamp(1.0 - shade - min(g, 0.0), light, 1.0);
  gl_FragColor = vec4(vec3(light), alpha);
}
`
