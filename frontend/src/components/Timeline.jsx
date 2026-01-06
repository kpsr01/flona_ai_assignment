import React from 'react';

const Timeline = ({ duration, transcript, insertions }) => {
  if (!duration) return null;

  const getLeftPosition = (time) => `${(time / duration) * 100}%`;
  const getWidth = (startTime, endTime) => `${((endTime - startTime) / duration) * 100}%`;

  return (
    <div className="bg-slate-800 rounded-lg p-4">
      <h3 className="text-lg font-semibold text-white mb-4">Timeline</h3>
      
      {/* Time markers */}
      <div className="relative h-6 mb-2">
        {[0, 0.25, 0.5, 0.75, 1].map((ratio) => (
          <div
            key={ratio}
            className="absolute text-xs text-slate-400"
            style={{ left: `${ratio * 100}%`, transform: 'translateX(-50%)' }}
          >
            {(duration * ratio).toFixed(1)}s
          </div>
        ))}
      </div>

      {/* A-roll track */}
      <div className="mb-2">
        <div className="text-xs text-slate-400 mb-1">A-Roll (Audio)</div>
        <div className="timeline-track bg-blue-900/50">
          {transcript?.map((seg, i) => (
            <div
              key={i}
              className="timeline-segment bg-blue-600/30 border-r border-blue-500/30"
              style={{
                left: getLeftPosition(seg.start_sec),
                width: getWidth(seg.start_sec, seg.end_sec),
              }}
              title={seg.text}
            />
          ))}
        </div>
      </div>

      {/* B-roll track */}
      <div>
        <div className="text-xs text-slate-400 mb-1">B-Roll Insertions</div>
        <div className="timeline-track">
          {insertions?.map((ins, i) => (
            <div
              key={i}
              className="broll-marker"
              style={{
                left: getLeftPosition(ins.start_sec),
                width: getWidth(ins.start_sec, ins.start_sec + ins.duration_sec),
              }}
              title={`${ins.broll_id}: ${ins.reason}`}
            >
              {ins.broll_id.replace('broll_', 'B')}
            </div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="flex gap-4 mt-4 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-blue-600/50 rounded" />
          <span className="text-slate-400">Transcript Segments</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-green-500 rounded" />
          <span className="text-slate-400">B-Roll Insertions</span>
        </div>
      </div>
    </div>
  );
};

export default Timeline;
