<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { GraphChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { ComposeOption } from 'echarts/core'
import type { GraphSeriesOption } from 'echarts/charts'
import type { TooltipComponentOption, LegendComponentOption } from 'echarts/components'

type ECOption = ComposeOption<GraphSeriesOption | TooltipComponentOption | LegendComponentOption>

echarts.use([GraphChart, TooltipComponent, LegendComponent, CanvasRenderer])

/** 与后端 query_neo4j_graph 返回的 nodes / links 对齐 */
export interface GraphNode {
  id: string
  label: string
  type: string
}

export interface GraphLink {
  source: string
  target: string
  rel: string
}

export interface GraphPayload {
  nodes?: GraphNode[]
  links?: GraphLink[]
  category?: string
  subcategory?: string
  message?: string
  source?: string
}

const props = defineProps<{
  /** 后端图谱 JSON；字符串表示提示/错误文案 */
  data: GraphPayload | string | null
  loading?: boolean
}>()

const chartRef = ref<HTMLDivElement | null>(null)
let chart: echarts.EChartsType | null = null
let resizeObserver: ResizeObserver | null = null

/** Neo4j Browser 风格：按节点类型着色 */
const TYPE_STYLE: Record<string, { color: string; size: number; legend: string }> = {
  category: { color: '#018BFF', size: 58, legend: '大类' },
  subcategory: { color: '#F16667', size: 46, legend: '小类' },
  song: { color: '#68BDF6', size: 34, legend: '歌曲' },
  entity: { color: '#FFC454', size: 36, legend: '关联实体' },
}

const DEFAULT_STYLE = { color: '#A5ABB6', size: 30, legend: '其他' }

const hintText = computed(() => {
  if (props.loading) return '图谱加载中…'
  if (typeof props.data === 'string') return props.data
  if (!props.data) return '请选择音乐大类与小类后点击确认'
  if (!props.data.nodes?.length) return props.data.message || '暂无图谱数据'
  return ''
})

const hasGraph = computed(
  () => typeof props.data === 'object' && !!props.data?.nodes?.length && !props.loading,
)

function styleOf(type: string) {
  return TYPE_STYLE[type] || DEFAULT_STYLE
}

function buildOption(payload: GraphPayload): ECOption {
  const nodes = payload.nodes || []
  const links = payload.links || []
  const categories = [
    ...new Map(
      nodes.map((n) => {
        const s = styleOf(n.type)
        return [n.type, { name: s.legend }]
      }),
    ).values(),
  ]
  const typeIndex = new Map(categories.map((c, i) => [c.name, i]))

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(15, 23, 32, 0.92)',
      borderColor: '#3a4654',
      textStyle: { color: '#e8eef5', fontSize: 12 },
      formatter: (params: unknown) => {
        const p = params as {
          dataType?: string
          name?: string
          data?: { type?: string; rel?: string; source?: string; target?: string }
        }
        if (p.dataType === 'edge') {
          return `<div style="font-weight:600">${p.data?.rel || '关系'}</div>
            <div style="opacity:.8;margin-top:4px">${p.data?.source} → ${p.data?.target}</div>`
        }
        const t = p.data?.type || ''
        return `<div style="font-weight:600">${p.name}</div>
          <div style="opacity:.8;margin-top:4px">类型：${styleOf(t).legend}</div>`
      },
    },
    legend: {
      data: categories.map((c) => c.name),
      orient: 'horizontal',
      bottom: 4,
      left: 'center',
      textStyle: { color: '#9aa7b5', fontSize: 11 },
      itemWidth: 10,
      itemHeight: 10,
      itemGap: 14,
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        roam: true,
        draggable: true,
        categories,
        data: nodes.map((n) => {
          const s = styleOf(n.type)
          return {
            id: n.id,
            name: n.label,
            type: n.type,
            category: typeIndex.get(s.legend) ?? 0,
            symbolSize: s.size,
            itemStyle: {
              color: s.color,
              borderColor: '#0f1720',
              borderWidth: 2,
              shadowBlur: 12,
              shadowColor: `${s.color}66`,
            },
            label: {
              show: true,
              color: '#e8eef5',
              fontSize: n.type === 'category' ? 13 : 11,
              fontWeight: n.type === 'category' ? 600 : 400,
              position: 'bottom',
              distance: 6,
            },
          }
        }),
        links: links.map((l) => ({
          source: l.source,
          target: l.target,
          rel: l.rel,
          label: {
            show: true,
            formatter: l.rel,
            color: '#7d8b9a',
            fontSize: 10,
            backgroundColor: 'rgba(15, 23, 32, 0.65)',
            padding: [2, 4],
          },
          lineStyle: {
            color: '#5a6a7a',
            curveness: 0.15,
            width: 1.5,
            opacity: 0.85,
          },
        })),
        force: {
          repulsion: 280,
          gravity: 0.08,
          edgeLength: [70, 140],
          friction: 0.2,
          layoutAnimation: true,
        },
        emphasis: {
          focus: 'adjacency',
          lineStyle: { width: 3, color: '#c8d4e0' },
          itemStyle: { borderColor: '#fff', borderWidth: 2 },
        },
        edgeSymbol: ['none', 'arrow'],
        edgeSymbolSize: [0, 8],
      },
    ],
  }
}

function renderChart() {
  if (!chartRef.value || !hasGraph.value || typeof props.data !== 'object' || !props.data) {
    chart?.clear()
    return
  }
  if (!chart) {
    chart = echarts.init(chartRef.value, undefined, { renderer: 'canvas' })
  }
  chart.setOption(buildOption(props.data), true)
}

function handleResize() {
  chart?.resize()
}

watch(
  () => props.data,
  () => renderChart(),
  { deep: true },
)

watch(
  () => props.loading,
  () => {
    if (!props.loading) renderChart()
  },
)

onMounted(() => {
  renderChart()
  window.addEventListener('resize', handleResize)
  if (chartRef.value) {
    resizeObserver = new ResizeObserver(() => handleResize())
    resizeObserver.observe(chartRef.value)
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  resizeObserver?.disconnect()
  resizeObserver = null
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div class="neo4j-view">
    <div v-if="hintText" class="neo4j-hint">{{ hintText }}</div>
    <div ref="chartRef" class="neo4j-chart" :class="{ hidden: !hasGraph }" />
    <div v-if="hasGraph && typeof data === 'object' && data?.message" class="neo4j-badge">
      {{ data.message }}
    </div>
  </div>
</template>

<style scoped>
.neo4j-view {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 280px;
  background:
    radial-gradient(ellipse at 20% 20%, rgba(1, 139, 255, 0.08), transparent 45%),
    radial-gradient(ellipse at 80% 70%, rgba(241, 102, 103, 0.07), transparent 40%),
    #1a2332;
  overflow: hidden;
}

.neo4j-chart {
  width: 100%;
  height: 100%;
  min-height: 280px;
}

.neo4j-chart.hidden {
  position: absolute;
  inset: 0;
  opacity: 0;
  pointer-events: none;
}

.neo4j-hint {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  text-align: center;
  color: #9aa7b5;
  font-size: 0.92rem;
  line-height: 1.6;
  z-index: 1;
}

.neo4j-badge {
  position: absolute;
  left: 10px;
  top: 10px;
  max-width: calc(100% - 20px);
  padding: 4px 8px;
  border-radius: 4px;
  background: rgba(15, 23, 32, 0.72);
  border: 1px solid #3a4654;
  color: #8a97a6;
  font-size: 0.72rem;
  line-height: 1.4;
  z-index: 2;
  pointer-events: none;
}
</style>
