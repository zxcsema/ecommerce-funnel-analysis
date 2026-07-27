with views as (
    select
        visitorid,
        min(event_time) as view_time
    from events
    where event = 'view'
    group by visitorid
),
carts as (
    select
        e.visitorid,
        min(e.event_time) as cart_time
    from events e
    inner join views v
        on e.visitorid = v.visitorid
    where e.event = 'addtocart'
      and e.event_time >= v.view_time
    group by e.visitorid
),
transactions as (
    select
        e.visitorid,
        min(e.event_time) as transaction_time
    from events e
    inner join carts c
        on e.visitorid = c.visitorid
    where e.event = 'transaction'
      and e.event_time >= c.cart_time
    group by e.visitorid
)
select
    v.visitorid,
    v.view_time,
    c.cart_time,
    t.transaction_time
from views v
left join carts c
    on v.visitorid = c.visitorid
left join transactions t
    on v.visitorid = t.visitorid
order by v.visitorid;
