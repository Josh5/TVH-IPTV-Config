import {ref, onBeforeUnmount} from 'vue'
import {Notify} from 'quasar'


export default function pollForBackgroundTasks() {
  const pendingTasks = ref([])
  const notifications = ref({})
  let timerId = null

  const displayCurrentTask = (messageId, taskName) => {
    if (!(messageId in notifications.value)) {
      notifications.value[messageId] = Notify.create({
        group: false,
        type: 'ongoing',
        position: 'bottom-left',
        message: `Executing background task: ${taskName}`,
        html: true,
      })
    } else {
      // Update the current status message
      notifications.value[messageId]({
        message: `Executing background task: ${taskName}`,
        html: true,
      })
    }
  }
  const dismissMessages = (messageId) => {
    if (typeof notifications.value === 'undefined') {
      return
    }
    if (typeof notifications.value[messageId] === 'function') {
      notifications.value[messageId]();
    }
    if (typeof notifications.value[messageId] !== 'undefined') {
      delete notifications.value[messageId]
    }
  }

  async function fetchData() {
    const response = await fetch('/tic-api/get-background-tasks')
    if (response.ok) {
      let payload = await response.json()
      let tasks = []
      if (payload.data['current_task']) {
        tasks.push({
          'icon': 'pending',
          'name': payload.data['current_task'],
        })
      }
      for (let i in payload.data['pending_tasks']) {
        tasks.push({
          'icon': 'radio_button_unchecked',
          'name': payload.data['pending_tasks'][i],
        })
      }
      pendingTasks.value = tasks
      if (payload.data['current_task']) {
        displayCurrentTask('currentTask', payload.data['current_task'])
      } else {
        dismissMessages('currentTask')
      }
    }
    startTimer()
  }

  function startTimer() {
    timerId = setTimeout(fetchData, 1000)
  }

  function stopTimer() {
    clearTimeout(timerId)
    dismissMessages('currentTask')
  }

  fetchData()

  onBeforeUnmount(() => {
    stopTimer()
  })

  return {
    pendingTasks
  }
}
