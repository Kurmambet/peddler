// src/utils/compressor.ts

export async function compressImage(
  file: File,
  quality: number = 0.75,
  maxWidth: number = 1920,
  maxHeight: number = 1920
): Promise<File> {
  // Если это не картинка, возвращаем как есть
  if (!file.type.startsWith("image/")) return file;
  // Если это GIF, не трогаем (иначе станет статичным кадром)
  if (file.type === "image/gif") return file;

  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = (event) => {
      const img = new Image();
      img.src = event.target?.result as string;
      img.onload = () => {
        // 1. Вычисляем новые размеры, сохраняя пропорции
        let w = img.width;
        let h = img.height;

        if (w > maxWidth || h > maxHeight) {
          const ratio = w / h;
          if (w > maxWidth) {
            w = maxWidth;
            h = Math.floor(w / ratio);
          }
          if (h > maxHeight) {
            h = maxHeight;
            w = Math.floor(h * ratio);
          }
        }

        // 2. Рисуем на Canvas
        const canvas = document.createElement("canvas");
        canvas.width = w;
        canvas.height = h;
        const ctx = canvas.getContext("2d");
        if (!ctx) {
          resolve(file); // Fallback
          return;
        }
        ctx.drawImage(img, 0, 0, w, h);

        // 3. Экспортируем в Blob -> File
        // force jpeg для лучшего сжатия, даже если был png (если прозрачность не критична)
        // Но лучше оставлять тип исходника, если это png
        const outputType =
          file.type === "image/png" ? "image/png" : "image/jpeg";

        canvas.toBlob(
          (blob) => {
            if (!blob) {
              resolve(file);
              return;
            }
            // Создаем новый файл с тем же именем
            const compressedFile = new File([blob], file.name, {
              type: outputType,
              lastModified: Date.now(),
            });

            console.log(
              `[Compressor] ${file.name}: ${(file.size / 1024).toFixed(
                0
              )}KB -> ${(compressedFile.size / 1024).toFixed(0)}KB`
            );
            resolve(compressedFile);
          },
          outputType,
          quality
        );
      };
      img.onerror = (err) => reject(err);
    };
    reader.onerror = (err) => reject(err);
  });
}
