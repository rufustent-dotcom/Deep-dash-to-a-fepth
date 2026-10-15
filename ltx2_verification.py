import math

# =====================================================================
# SUBSET 1: Audio & Video VAE Latent Space & Compression Verification
# =====================================================================
class LatentCompressionSpec:
    """
    Calculates and verifies the exact spatiotemporal (3D) and temporal (1D)
    compression ratios and token alignments between Video and Audio VAEs.
    """
    def __init__(self, duration_sec=1.0, fps=25, height=128, width=128, audio_sr=16000):
        self.duration_sec = duration_sec
        self.fps = fps
        self.H = height
        self.W = width
        self.audio_sr = audio_sr

    def compute_specs(self):
        # 1. Video Latent Math (8x8x8 Spatiotemporal Compression)
        raw_frames = int(self.duration_sec * self.fps)
        t_vid_latent = math.ceil(raw_frames / 8)
        h_latent = self.H // 8
        w_latent = self.W // 8
        n_video_tokens = t_vid_latent * h_latent * w_latent
        video_vol_compression = 8 * 8 * 8  # 512:1

        # 2. Audio Latent Math (25 tokens/sec -> 40ms step, 128-dim)
        raw_stereo_samples = int(self.duration_sec * self.audio_sr * 2)
        n_audio_tokens = int(self.duration_sec * 25)  # 1/25s per token
        d_audio_vae = 128
        audio_latent_floats = n_audio_tokens * d_audio_vae
        audio_compression_ratio = raw_stereo_samples / audio_latent_floats  # 10:1

        # 3. Physical Timestamps (in elapsed seconds) for 1D Temporal RoPE
        # Linear spacing along [0, duration_sec]
        video_timestamps = [i * (self.duration_sec / max(1, t_vid_latent - 1)) for i in range(t_vid_latent)]
        video_token_times = []
        for t in video_timestamps:
            video_token_times.extend([t] * (h_latent * w_latent))
            
        audio_token_times = [i * (self.duration_sec / max(1, n_audio_tokens - 1)) for i in range(n_audio_tokens)]

        return {
            "n_video_tokens": n_video_tokens,
            "video_grid": (t_vid_latent, h_latent, w_latent),
            "video_compression": f"{video_vol_compression}:1",
            "n_audio_tokens": n_audio_tokens,
            "audio_compression": f"{audio_compression_ratio:.1f}:1",
            "video_token_times_len": len(video_token_times),
            "audio_token_times_len": len(audio_token_times),
            "time_range": (0.0, self.duration_sec)
        }

if __name__ == "__main__":
    print("=" * 72)
    print("LTX-2 ARCHITECTURAL & MATHEMATICAL VERIFICATION PIPELINE")
    print("=" * 72)
    spec = LatentCompressionSpec(duration_sec=1.0, fps=25, height=128, width=128)
    res = spec.compute_specs()
    print("\n[Subset 1] VAE Latent Compression & Alignment:")
    print(f"  - Video Spatiotemporal Compression : {res['video_compression']} (Grid: {res['video_grid']} -> {res['n_video_tokens']} tokens)")
    print(f"  - Audio Stereo Latent Compression  : {res['audio_compression']} ({res['n_audio_tokens']} tokens @ 25Hz / 40ms step)")
    print(f"  - Video Token Timestamps           : {res['video_token_times_len']} points synchronized across spatial grid")
    print(f"  - Audio Token Timestamps           : {res['audio_token_times_len']} points spaced across continuous elapsed time [0, {res['time_range'][1]}s]")
    print("=" * 72)
