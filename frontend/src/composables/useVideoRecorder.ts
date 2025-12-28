// frontend/src/composables/useVideoRecorder.ts
import { ref } from "vue";

export function useVideoRecorder() {
  const isRecording = ref(false);
  const recordingDuration = ref(0);
  const stream = ref<MediaStream | null>(null);

  let mediaRecorder: MediaRecorder | null = null;
  let chunks: Blob[] = [];
  let timer: any = null;

  const stopAllTracks = () => {
    if (stream.value) {
      stream.value.getTracks().forEach((track) => {
        track.stop();
        // В Firefox важно явно отключать треки перед stop()
        track.enabled = false;
      });
      stream.value = null;
    }
  };

  const startRecording = async () => {
    try {
      stopAllTracks(); // Чистим перед стартом

      // ФИКС ДЛЯ FIREFOX:
      // Убираем требования к разрешению. Firefox сам выберет оптимальное (обычно 640x480).
      // CSS object-fit: cover сделает видео квадратным визуально.
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: true,
        video: {
          facingMode: "user",
          // frameRate можно оставить, это обычно не ломает
          frameRate: { ideal: 30 },
        },
      });

      stream.value = mediaStream;
      chunks = [];

      // Приоритет кодеков: VP8 самый совместимый для Chrome <-> Firefox
      const types = [
        "video/webm;codecs=vp8,opus",
        "video/webm;codecs=vp8",
        "video/webm",
      ];
      const mimeType =
        types.find((type) => MediaRecorder.isTypeSupported(type)) || "";
      console.log("[VideoRecorder] Using mimeType:", mimeType);

      mediaRecorder = new MediaRecorder(mediaStream, {
        mimeType,
        videoBitsPerSecond: 1500000, // 1.5 Mbps для хорошего качества
      });

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.push(e.data);
      };

      // Timeslice 1000мс обязателен для создания Clusters
      mediaRecorder.start(1000);
      isRecording.value = true;

      const startTs = Date.now();
      timer = setInterval(() => {
        recordingDuration.value = Math.floor((Date.now() - startTs) / 1000);
      }, 1000);
    } catch (err) {
      console.error("Camera access error:", err);
      stopAllTracks(); // Чистим, если упало
      throw err;
    }
  };

  const stopRecording = (): Promise<{ blob: Blob; duration: number }> => {
    return new Promise((resolve) => {
      if (!mediaRecorder) return;

      mediaRecorder.onstop = () => {
        const finalBlob = new Blob(chunks, { type: mediaRecorder?.mimeType });
        const finalDuration = recordingDuration.value;
        stopAllTracks();
        isRecording.value = false;
        recordingDuration.value = 0;
        if (timer) clearInterval(timer);
        resolve({ blob: finalBlob, duration: finalDuration });
      };

      mediaRecorder.stop();
    });
  };

  const cancelRecording = () => {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
    }
    stopAllTracks();
    isRecording.value = false;
    recordingDuration.value = 0;
    if (timer) clearInterval(timer);
  };

  return {
    isRecording,
    recordingDuration,
    stream,
    startRecording,
    stopRecording,
    cancelRecording,
  };
}
