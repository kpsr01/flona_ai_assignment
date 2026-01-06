import React from 'react';
import { Film, Clock } from 'lucide-react';

const VideoPreview = ({ url, title, metadata, duration }) => {
  return (
    <div className="bg-slate-800 rounded-lg overflow-hidden">
      <div className="aspect-video bg-slate-900 relative">
        <video 
          src={url} 
          className="w-full h-full object-cover"
          controls
          preload="metadata"
        />
        {duration && (
          <div className="absolute bottom-2 right-2 bg-black/70 px-2 py-1 rounded text-xs text-white flex items-center gap-1">
            <Clock size={12} />
            {duration.toFixed(1)}s
          </div>
        )}
      </div>
      <div className="p-3">
        <h4 className="font-medium text-white flex items-center gap-2">
          <Film size={16} className="text-green-400" />
          {title}
        </h4>
        {metadata && (
          <p className="text-sm text-slate-400 mt-1 line-clamp-2">{metadata}</p>
        )}
      </div>
    </div>
  );
};

export default VideoPreview;
