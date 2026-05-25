// Mock data for development — matches backend OrderResponse / OrderDrawerResponse schemas

export const mockOrders = [
  { id: 1, number: '26-0117', customer_id: 1, customer_name: 'Магнит, ТТ Авиаторов',       delivery_address: 'г. Красноярск, ул. Авиаторов, 25',   delivery_date: '2026-05-14', status: 'assembly',    delivery_user_id: 5, delivery_user_name: 'Сидоров А.П.', comment: 'Звонить за час до доставки', created_at: '2026-05-12T08:00:00' },
  { id: 2, number: '26-0118', customer_id: 2, customer_name: 'Пятёрочка, ТТ Свободный',    delivery_address: 'г. Красноярск, пр. Свободный, 64',    delivery_date: '2026-05-15', status: 'production',  delivery_user_id: null, delivery_user_name: null, comment: '', created_at: '2026-05-13T09:00:00' },
  { id: 3, number: '26-0119', customer_id: 3, customer_name: 'ИП Соколова О.В.',           delivery_address: 'г. Красноярск, ул. Партизана Железняка, 10', delivery_date: '2026-05-16', status: 'created', delivery_user_id: null, delivery_user_name: null, comment: '', created_at: '2026-05-14T10:00:00' },
  { id: 4, number: '26-0120', customer_id: 1, customer_name: 'Магнит, ТТ Северный',        delivery_address: 'г. Красноярск, ул. Северная, 5',      delivery_date: '2026-05-16', status: 'production',  delivery_user_id: null, delivery_user_name: null, comment: '', created_at: '2026-05-14T11:00:00' },
  { id: 5, number: '26-0121', customer_id: 4, customer_name: 'Лента, ТТ Взлётка',          delivery_address: 'г. Красноярск, ул. Взлётная, 99',     delivery_date: '2026-05-17', status: 'delivery',    delivery_user_id: 5, delivery_user_name: 'Иванов А.А.', comment: '', created_at: '2026-05-13T08:00:00' },
  { id: 6, number: '26-0122', customer_id: 5, customer_name: 'ИП Гаврилов А.С.',           delivery_address: 'г. Красноярск, ул. Гагарина, 7',      delivery_date: '2026-05-18', status: 'created',     delivery_user_id: null, delivery_user_name: null, comment: '', created_at: '2026-05-15T08:00:00' },
  { id: 7, number: '26-0123', customer_id: 2, customer_name: 'Пятёрочка, ТТ Семафорная',   delivery_address: 'г. Красноярск, ул. Семафорная, 22',   delivery_date: '2026-05-19', status: 'production',  delivery_user_id: null, delivery_user_name: null, comment: '', created_at: '2026-05-15T09:00:00' },
  { id: 8, number: '26-0124', customer_id: 1, customer_name: 'Магнит, ТТ Партизана',       delivery_address: 'г. Красноярск, ул. Партизана Железняка, 2', delivery_date: '2026-05-20', status: 'created', delivery_user_id: null, delivery_user_name: null, comment: '', created_at: '2026-05-16T08:00:00' },
  { id: 9, number: '26-0125', customer_id: 6, customer_name: 'ООО «Кафе-бар»',             delivery_address: 'г. Красноярск, пр. Мира, 5',          delivery_date: '2026-05-21', status: 'completed',   delivery_user_id: 5, delivery_user_name: 'Петров В.В.', comment: '', created_at: '2026-05-10T08:00:00' },
]

// Drawer data per order id — matches OrderDrawerResponse
export const mockDrawers = {
  1: {
    order: null, // filled dynamically from mockOrders
    items: [
      { id: 1, order_id: 1, product_id: 1, product_name: 'Молоко 3,2% 1л',    units_per_box: 12, quantity: 40 },
      { id: 2, order_id: 1, product_id: 2, product_name: 'Кефир 1% 1л',        units_per_box: 12, quantity: 20 },
      { id: 3, order_id: 1, product_id: 3, product_name: 'Сметана 20% 200г',   units_per_box: 24, quantity: 10 },
    ],
    reservations_by_item: {
      '1': [{ reservation_id: 1, stock_id: 1, batch_label: 'П-26-04-18', quantity: 480 }],
      '2': [{ reservation_id: 2, stock_id: 2, batch_label: 'П-26-04-22', quantity: 240 }],
      '3': [{ reservation_id: 3, stock_id: 3, batch_label: 'П-26-05-02', quantity: 240 }],
    },
    tasks: [],
  },
  2: {
    order: null,
    items: [
      { id: 4, order_id: 2, product_id: 1, product_name: 'Молоко 3,2% 1л',            units_per_box: 12, quantity: 40 },
      { id: 5, order_id: 2, product_id: 4, product_name: 'Йогурт «Питьевой» клубника', units_per_box: 12, quantity: 20 },
    ],
    reservations_by_item: {},
    tasks: [
      { task_id: 79, product_name: 'Молоко 3,2%',           quantity: 40, executor_name: 'Сидоров А.П.', deadline: '2026-05-14', status: 'in_progress' },
      { task_id: 80, product_name: 'Йогурт клубника 0,9л',  quantity: 20, executor_name: 'Иванов Д.К.',  deadline: '2026-05-14', status: 'created' },
    ],
  },
}

export const mockTasks = [
  { id: 1, product: 'Сахар фасованный 1кг', quantity: 500, unit: 'шт', executor: 'Иванова М.П.', status: 'in_progress', type: 'packaging', planned_start: '2024-01-15', planned_end: '2024-01-16', actual_start: '2024-01-15 09:00', actual_end: null, order_id: 2, stops: [], consumptions: [{ material: 'Сахар-песок', planned: 510, actual: 505, unit: 'кг' }] },
  { id: 2, product: 'Мука в/с 2кг', quantity: 300, unit: 'шт', executor: 'Петров А.С.', status: 'created', type: 'packaging', planned_start: '2024-01-16', planned_end: '2024-01-17', actual_start: null, actual_end: null, order_id: 8, stops: [], consumptions: [] },
  { id: 3, product: 'Соль йодированная 1кг', quantity: 200, unit: 'шт', executor: 'Сидорова Е.В.', status: 'stopped', type: 'packaging', planned_start: '2024-01-14', planned_end: '2024-01-15', actual_start: '2024-01-14 08:30', actual_end: null, order_id: null, stops: [{ reason: 'Нет сырья', started_at: '2024-01-14 15:00', ended_at: null }], consumptions: [] },
  { id: 4, product: 'Сахар фасованный 5кг', quantity: 100, unit: 'шт', executor: 'Иванова М.П.', status: 'completed', type: 'packaging', planned_start: '2024-01-13', planned_end: '2024-01-14', actual_start: '2024-01-13 09:00', actual_end: '2024-01-13 17:00', order_id: 3, stops: [], consumptions: [{ material: 'Сахар-песок', planned: 505, actual: 502, unit: 'кг' }] },
  { id: 5, product: 'Мука в/с 1кг', quantity: 400, unit: 'шт', executor: 'Козлов Д.Н.', status: 'closed', type: 'packaging', planned_start: '2024-01-11', planned_end: '2024-01-12', actual_start: '2024-01-11 09:00', actual_end: '2024-01-11 18:00', order_id: 5, stops: [], consumptions: [{ material: 'Мука пшеничная', planned: 405, actual: 400, unit: 'кг' }] },
  { id: 6, product: 'Соль пищевая 1кг', quantity: 150, unit: 'шт', executor: 'Петров А.С.', status: 'in_progress', type: 'packaging', planned_start: '2024-01-15', planned_end: '2024-01-16', actual_start: '2024-01-15 10:00', actual_end: null, order_id: 4, stops: [], consumptions: [] },
  { id: 7, product: 'Сахар фасованный 1кг', quantity: 600, unit: 'шт', executor: 'Сидорова Е.В.', status: 'created', type: 'packaging', planned_start: '2024-01-17', planned_end: '2024-01-18', actual_start: null, actual_end: null, order_id: 7, stops: [], consumptions: [] },
  { id: 8, product: 'Мука в/с 2кг', quantity: 250, unit: 'шт', executor: 'Козлов Д.Н.', status: 'in_progress', type: 'packaging', planned_start: '2024-01-15', planned_end: '2024-01-17', actual_start: '2024-01-15 11:00', actual_end: null, order_id: 1, stops: [], consumptions: [] },
]

export const mockWarehouseRaw = [
  { id: 1, name: 'Сахар-песок', unit: 'кг', batches: [{ id: 1, quantity: 500, expiry_date: '2024-03-01', reserved: 200 }, { id: 2, quantity: 300, expiry_date: '2024-06-15', reserved: 100 }], critical_stock: 200 },
  { id: 2, name: 'Мука пшеничная в/с', unit: 'кг', batches: [{ id: 3, quantity: 800, expiry_date: '2024-02-10', reserved: 300 }], critical_stock: 300 },
  { id: 3, name: 'Соль пищевая', unit: 'кг', batches: [{ id: 4, quantity: 150, expiry_date: '2025-01-01', reserved: 60 }], critical_stock: 200 },
  { id: 4, name: 'Сода пищевая', unit: 'кг', batches: [{ id: 5, quantity: 50, expiry_date: '2024-01-20', reserved: 0 }], critical_stock: 100 },
  { id: 5, name: 'Крахмал картофельный', unit: 'кг', batches: [{ id: 6, quantity: 200, expiry_date: '2024-04-30', reserved: 50 }], critical_stock: 50 },
]

export const mockWarehousePackaging = [
  { id: 1, name: 'Пакет 1кг прозрачный', unit: 'шт', quantity: 5000, critical_stock: 2000 },
  { id: 2, name: 'Пакет 2кг прозрачный', unit: 'шт', quantity: 3000, critical_stock: 1500 },
  { id: 3, name: 'Пакет 5кг прозрачный', unit: 'шт', quantity: 800, critical_stock: 1000 },
  { id: 4, name: 'Коробка гофро 10кг', unit: 'шт', quantity: 200, critical_stock: 100 },
  { id: 5, name: 'Скотч упаковочный', unit: 'рул', quantity: 15, critical_stock: 20 },
  { id: 6, name: 'Этикетка сахар 1кг', unit: 'шт', quantity: 4000, critical_stock: 2000 },
]

export const mockWarehouseProducts = [
  { id: 1, name: 'Сахар фасованный 1кг', unit: 'шт', batches: [{ id: 1, quantity: 300, produced_at: '2024-01-10', reserved: 100 }, { id: 2, quantity: 200, produced_at: '2024-01-13', reserved: 50 }] },
  { id: 2, name: 'Мука в/с 2кг', unit: 'шт', batches: [{ id: 3, quantity: 150, produced_at: '2024-01-11', reserved: 100 }] },
  { id: 3, name: 'Соль йодированная 1кг', unit: 'шт', batches: [{ id: 4, quantity: 80, produced_at: '2024-01-12', reserved: 40 }] },
  { id: 4, name: 'Сахар фасованный 5кг', unit: 'шт', batches: [{ id: 5, quantity: 50, produced_at: '2024-01-13', reserved: 30 }] },
]

export const mockReferences = {
  rawMaterials: [
    { id: 1, name: 'Сахар-песок', unit: 'кг', shelf_life_days: 730, critical_stock: 200, is_active: true },
    { id: 2, name: 'Мука пшеничная в/с', unit: 'кг', shelf_life_days: 180, critical_stock: 300, is_active: true },
    { id: 3, name: 'Соль пищевая', unit: 'кг', shelf_life_days: 1825, critical_stock: 200, is_active: true },
    { id: 4, name: 'Сода пищевая', unit: 'кг', shelf_life_days: 365, critical_stock: 100, is_active: true },
    { id: 5, name: 'Крахмал картофельный', unit: 'кг', shelf_life_days: 540, critical_stock: 50, is_active: false },
  ],
  packaging: [
    { id: 1, name: 'Пакет 1кг прозрачный', unit: 'шт', critical_stock: 2000, is_active: true },
    { id: 2, name: 'Пакет 2кг прозрачный', unit: 'шт', critical_stock: 1500, is_active: true },
    { id: 3, name: 'Пакет 5кг прозрачный', unit: 'шт', critical_stock: 1000, is_active: true },
    { id: 4, name: 'Коробка гофро 10кг', unit: 'шт', critical_stock: 100, is_active: true },
    { id: 5, name: 'Скотч упаковочный', unit: 'рул', critical_stock: 20, is_active: true },
  ],
  products: [
    { id: 1, name: 'Сахар фасованный 1кг', unit: 'шт', units_per_box: 10, shelf_life_days: 730, critical_stock: 100, is_active: true },
    { id: 2, name: 'Мука в/с 2кг', unit: 'шт', units_per_box: 6, shelf_life_days: 180, critical_stock: 50, is_active: true },
    { id: 3, name: 'Соль йодированная 1кг', unit: 'шт', units_per_box: 12, shelf_life_days: 1825, critical_stock: 80, is_active: true },
    { id: 4, name: 'Сахар фасованный 5кг', unit: 'шт', units_per_box: 4, shelf_life_days: 730, critical_stock: 30, is_active: true },
  ],
  customers: [
    { id: 1, name: 'ИП Сидоров', address: 'ул. Ленина, 10', contact: '+7 901 123-45-67', comment: '', is_active: true },
    { id: 2, name: 'ООО Продторг', address: 'пр. Мира, 5', contact: '+7 902 234-56-78', comment: 'Крупный клиент', is_active: true },
    { id: 3, name: 'ИП Петрова', address: 'ул. Советская, 22', contact: '+7 903 345-67-89', comment: '', is_active: true },
    { id: 4, name: 'ЗАО Торгсервис', address: 'ул. Гагарина, 7', contact: '+7 904 456-78-90', comment: '', is_active: true },
    { id: 5, name: 'ИП Козлов', address: 'ул. Пушкина, 3', contact: '+7 905 567-89-01', comment: '', is_active: false },
  ],
  recipes: [
    { id: 1, product: 'Сахар фасованный 1кг', material: 'Сахар-песок', consumption: 1.01, waste_percent: 1.0 },
    { id: 2, product: 'Мука в/с 2кг', material: 'Мука пшеничная в/с', consumption: 2.02, waste_percent: 1.0 },
    { id: 3, product: 'Соль йодированная 1кг', material: 'Соль пищевая', consumption: 1.005, waste_percent: 0.5 },
    { id: 4, product: 'Сахар фасованный 5кг', material: 'Сахар-песок', consumption: 5.05, waste_percent: 1.0 },
  ],
  packagingSizes: [
    { id: 1, product: 'Сахар фасованный 1кг', packaging: 'Пакет 1кг прозрачный', units_per_pack: 1 },
    { id: 2, product: 'Мука в/с 2кг', packaging: 'Пакет 2кг прозрачный', units_per_pack: 1 },
    { id: 3, product: 'Соль йодированная 1кг', packaging: 'Пакет 1кг прозрачный', units_per_pack: 1 },
    { id: 4, product: 'Сахар фасованный 5кг', packaging: 'Пакет 5кг прозрачный', units_per_pack: 1 },
  ],
}

export const mockDeliveries = [
  { id: 1, order_id: 4, customer: 'ЗАО Торгсервис', address: 'ул. Гагарина, 7', status: 'in_transit', driver: 'Иванов А.А.', planned_date: '2024-01-18', picked_up_at: '2024-01-18 09:00', delivered_at: null, cancel_reason: null },
  { id: 2, order_id: 5, customer: 'ИП Козлов', address: 'ул. Пушкина, 3', status: 'completed', driver: 'Петров В.В.', planned_date: '2024-01-15', picked_up_at: '2024-01-15 10:00', delivered_at: '2024-01-15 14:30', cancel_reason: null },
  { id: 3, order_id: 3, customer: 'ИП Петрова', address: 'ул. Советская, 22', status: 'pending', driver: null, planned_date: '2024-01-19', picked_up_at: null, delivered_at: null, cancel_reason: null },
  { id: 4, order_id: 6, customer: 'ООО Альфа', address: 'пр. Победы, 1', status: 'cancelled', driver: 'Сидоров Н.К.', planned_date: '2024-01-14', picked_up_at: null, delivered_at: null, cancel_reason: 'Заказ отменён' },
]

export const mockUsers = [
  { id: 1, name: 'Иванова Ольга', email: 'admin@yarko.ru', roles: ['director', 'warehouse_manager'], telegram: '@olga_yarko', is_active: true },
  { id: 2, name: 'Петров Алексей', email: 'petrov@yarko.ru', roles: ['production_manager'], telegram: '@petrov_a', is_active: true },
  { id: 3, name: 'Сидорова Елена', email: 'sidorova@yarko.ru', roles: ['worker'], telegram: null, is_active: true },
  { id: 4, name: 'Козлов Дмитрий', email: 'kozlov@yarko.ru', roles: ['worker'], telegram: '@kozlov_d', is_active: false },
]
